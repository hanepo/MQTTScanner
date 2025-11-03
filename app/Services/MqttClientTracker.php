<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

/**
 * MQTT Client Tracker Service
 *
 * Tracks and identifies:
 * - Publishers (who publishes to which topics)
 * - Subscribers (who subscribes to which topics)
 * - Client activities and patterns
 */
class MqttClientTracker
{
    protected $cachePrefix = 'mqtt_tracker_';
    protected $cacheDuration = 3600; // 1 hour

    /**
     * Track a publisher
     *
     * @param string $clientId Client identifier
     * @param string $topic Topic being published to
     * @param array $metadata Additional metadata
     * @return void
     */
    public function trackPublisher($clientId, $topic, $metadata = [])
    {
        $key = $this->cachePrefix . 'publishers';
        $publishers = Cache::get($key, []);

        $publisherKey = $clientId . '::' . $topic;

        if (!isset($publishers[$publisherKey])) {
            $publishers[$publisherKey] = [
                'client_id' => $clientId,
                'topic' => $topic,
                'first_seen' => now()->toIso8601String(),
                'message_count' => 0,
                'last_message_time' => null,
                'metadata' => $metadata,
            ];
        }

        $publishers[$publisherKey]['message_count']++;
        $publishers[$publisherKey]['last_message_time'] = now()->toIso8601String();
        $publishers[$publisherKey]['metadata'] = array_merge(
            $publishers[$publisherKey]['metadata'],
            $metadata
        );

        Cache::put($key, $publishers, $this->cacheDuration);
    }

    /**
     * Track a subscriber
     *
     * @param string $clientId Client identifier
     * @param string $topic Topic being subscribed to
     * @param array $metadata Additional metadata
     * @return void
     */
    public function trackSubscriber($clientId, $topic, $metadata = [])
    {
        $key = $this->cachePrefix . 'subscribers';
        $subscribers = Cache::get($key, []);

        $subscriberKey = $clientId . '::' . $topic;

        if (!isset($subscribers[$subscriberKey])) {
            $subscribers[$subscriberKey] = [
                'client_id' => $clientId,
                'topic' => $topic,
                'subscribed_at' => now()->toIso8601String(),
                'active' => true,
                'metadata' => $metadata,
            ];
        }

        $subscribers[$subscriberKey]['active'] = true;
        $subscribers[$subscriberKey]['metadata'] = array_merge(
            $subscribers[$subscriberKey]['metadata'],
            $metadata
        );

        Cache::put($key, $subscribers, $this->cacheDuration);
    }

    /**
     * Get all publishers
     *
     * @param string|null $topic Filter by topic
     * @return array List of publishers
     */
    public function getPublishers($topic = null)
    {
        $key = $this->cachePrefix . 'publishers';
        $publishers = Cache::get($key, []);

        if ($topic) {
            return array_filter($publishers, function($pub) use ($topic) {
                return $pub['topic'] === $topic ||
                       $this->topicMatches($pub['topic'], $topic);
            });
        }

        return $publishers;
    }

    /**
     * Get all subscribers
     *
     * @param string|null $topic Filter by topic
     * @return array List of subscribers
     */
    public function getSubscribers($topic = null)
    {
        $key = $this->cachePrefix . 'subscribers';
        $subscribers = Cache::get($key, []);

        if ($topic) {
            return array_filter($subscribers, function($sub) use ($topic) {
                return $sub['topic'] === $topic ||
                       $this->topicMatches($topic, $sub['topic']);
            });
        }

        return $subscribers;
    }

    /**
     * Get detailed client information
     *
     * @param string $clientId Client identifier
     * @return array Client details
     */
    public function getClientDetails($clientId)
    {
        $publishers = $this->getPublishers();
        $subscribers = $this->getSubscribers();

        $clientPubs = array_filter($publishers, fn($p) => $p['client_id'] === $clientId);
        $clientSubs = array_filter($subscribers, fn($s) => $s['client_id'] === $clientId);

        return [
            'client_id' => $clientId,
            'is_publisher' => count($clientPubs) > 0,
            'is_subscriber' => count($clientSubs) > 0,
            'role' => $this->determineClientRole($clientPubs, $clientSubs),
            'published_topics' => array_values(array_column($clientPubs, 'topic')),
            'subscribed_topics' => array_values(array_column($clientSubs, 'topic')),
            'total_messages_published' => array_sum(array_column($clientPubs, 'message_count')),
            'publishers_count' => count($clientPubs),
            'subscribers_count' => count($clientSubs),
            'publishers' => array_values($clientPubs),
            'subscribers' => array_values($clientSubs),
        ];
    }

    /**
     * Determine client role based on activity
     *
     * @param array $publishers Publisher records
     * @param array $subscribers Subscriber records
     * @return string Client role
     */
    protected function determineClientRole($publishers, $subscribers)
    {
        $isPub = count($publishers) > 0;
        $isSub = count($subscribers) > 0;

        if ($isPub && $isSub) {
            return 'PUBLISHER_SUBSCRIBER';
        } elseif ($isPub) {
            return 'PUBLISHER_ONLY';
        } elseif ($isSub) {
            return 'SUBSCRIBER_ONLY';
        } else {
            return 'UNKNOWN';
        }
    }

    /**
     * Get topic statistics
     *
     * @param string $topic Topic name
     * @return array Topic statistics
     */
    public function getTopicStatistics($topic)
    {
        $publishers = $this->getPublishers($topic);
        $subscribers = $this->getSubscribers($topic);

        return [
            'topic' => $topic,
            'publisher_count' => count($publishers),
            'subscriber_count' => count($subscribers),
            'publishers' => array_values($publishers),
            'subscribers' => array_values($subscribers),
            'total_messages' => array_sum(array_column($publishers, 'message_count')),
            'most_active_publisher' => $this->getMostActivePublisher($publishers),
        ];
    }

    /**
     * Get most active publisher for a topic
     *
     * @param array $publishers Publisher list
     * @return array|null Most active publisher
     */
    protected function getMostActivePublisher($publishers)
    {
        if (empty($publishers)) {
            return null;
        }

        usort($publishers, function($a, $b) {
            return ($b['message_count'] ?? 0) - ($a['message_count'] ?? 0);
        });

        return $publishers[0] ?? null;
    }

    /**
     * Check if topic matches pattern (supports MQTT wildcards)
     *
     * @param string $topic Actual topic
     * @param string $pattern Topic pattern (with wildcards)
     * @return bool Whether topic matches pattern
     */
    protected function topicMatches($topic, $pattern)
    {
        // Convert MQTT wildcards to regex
        $pattern = str_replace(['#', '+'], ['.*', '[^/]+'], $pattern);
        $pattern = '/^' . str_replace('/', '\/', $pattern) . '$/';

        return preg_match($pattern, $topic) === 1;
    }

    /**
     * Analyze publisher/subscriber patterns
     *
     * @return array Pattern analysis
     */
    public function analyzePatterns()
    {
        $publishers = $this->getPublishers();
        $subscribers = $this->getSubscribers();

        // Detect potential security issues
        $securityIssues = [];

        // Check for wildcard subscribers
        foreach ($subscribers as $sub) {
            if (strpos($sub['topic'], '#') !== false) {
                $securityIssues[] = [
                    'type' => 'WILDCARD_SUBSCRIBER',
                    'severity' => 'MEDIUM',
                    'client_id' => $sub['client_id'],
                    'topic' => $sub['topic'],
                    'description' => 'Client subscribes to all topics using # wildcard',
                    'recommendation' => 'Restrict subscription to specific topics',
                ];
            }
        }

        // Check for unauthorized topic access patterns
        foreach ($publishers as $pub) {
            if (strpos($pub['topic'], '$SYS') === 0) {
                $securityIssues[] = [
                    'type' => 'SYS_TOPIC_PUBLISH',
                    'severity' => 'HIGH',
                    'client_id' => $pub['client_id'],
                    'topic' => $pub['topic'],
                    'description' => 'Client publishing to system topic',
                    'recommendation' => 'Configure ACL to prevent unauthorized system topic access',
                ];
            }
        }

        return [
            'total_publishers' => count($publishers),
            'total_subscribers' => count($subscribers),
            'unique_topics' => count(array_unique(array_merge(
                array_column($publishers, 'topic'),
                array_column($subscribers, 'topic')
            ))),
            'security_issues' => $securityIssues,
            'patterns' => [
                'most_popular_topic' => $this->getMostPopularTopic($publishers, $subscribers),
                'orphaned_topics' => $this->findOrphanedTopics($publishers, $subscribers),
            ],
        ];
    }

    /**
     * Find most popular topic
     *
     * @param array $publishers Publishers list
     * @param array $subscribers Subscribers list
     * @return array|null Most popular topic
     */
    protected function getMostPopularTopic($publishers, $subscribers)
    {
        $topicCounts = [];

        foreach ($publishers as $pub) {
            $topic = $pub['topic'];
            if (!isset($topicCounts[$topic])) {
                $topicCounts[$topic] = ['publishers' => 0, 'subscribers' => 0, 'total' => 0];
            }
            $topicCounts[$topic]['publishers']++;
            $topicCounts[$topic]['total']++;
        }

        foreach ($subscribers as $sub) {
            $topic = $sub['topic'];
            if (!isset($topicCounts[$topic])) {
                $topicCounts[$topic] = ['publishers' => 0, 'subscribers' => 0, 'total' => 0];
            }
            $topicCounts[$topic]['subscribers']++;
            $topicCounts[$topic]['total']++;
        }

        if (empty($topicCounts)) {
            return null;
        }

        arsort($topicCounts);
        $topTopic = array_key_first($topicCounts);

        return [
            'topic' => $topTopic,
            'publishers' => $topicCounts[$topTopic]['publishers'],
            'subscribers' => $topicCounts[$topTopic]['subscribers'],
            'total_activity' => $topicCounts[$topTopic]['total'],
        ];
    }

    /**
     * Find topics with publishers but no subscribers
     *
     * @param array $publishers Publishers list
     * @param array $subscribers Subscribers list
     * @return array List of orphaned topics
     */
    protected function findOrphanedTopics($publishers, $subscribers)
    {
        $publishedTopics = array_unique(array_column($publishers, 'topic'));
        $subscribedTopics = array_unique(array_column($subscribers, 'topic'));

        return array_values(array_diff($publishedTopics, $subscribedTopics));
    }

    /**
     * Simulate tracking for ESP32 sensor
     *
     * @return void
     */
    public function simulateEsp32Tracking()
    {
        // Track ESP32 as publisher
        $this->trackPublisher('esp32-multi-sensor', 'sensors/hanif/multi_secure', [
            'device_type' => 'ESP32',
            'firmware_version' => '1.0.0',
            'sensors' => ['DHT11', 'LDR', 'PIR'],
            'ip_address' => '192.168.100.50',
        ]);

        $this->trackPublisher('esp32-multi-sensor', 'sensors/hanif/dht11_secure', [
            'device_type' => 'ESP32',
            'firmware_version' => '1.0.0',
            'sensors' => ['DHT11'],
        ]);

        // Track Laravel scanner as subscriber
        $this->trackSubscriber('laravel-scanner', 'sensors/#', [
            'application' => 'Laravel MQTT Scanner',
            'version' => '1.0.0',
            'purpose' => 'Security Monitoring',
        ]);

        Log::info('Simulated ESP32 and Laravel scanner tracking');
    }
}
