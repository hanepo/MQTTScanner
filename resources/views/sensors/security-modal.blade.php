<!-- Security Details Modal -->
<div id="securityModal" class="hidden fixed inset-0 bg-gray-600 bg-opacity-75 overflow-y-auto h-full w-full z-50">
    <div class="relative top-10 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-lg bg-white">
        <!-- Modal Header -->
        <div class="flex justify-between items-center pb-3 border-b">
            <h3 class="text-2xl font-bold text-gray-900">🔒 MQTT Security Analysis Report</h3>
            <button id="closeModal" class="text-gray-400 hover:text-gray-600 text-3xl font-bold">&times;</button>
        </div>

        <!-- Modal Content -->
        <div id="securityContent" class="mt-4 max-h-[70vh] overflow-y-auto">
            <div class="text-center py-8">
                <svg class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-gray-600">Loading security analysis...</p>
            </div>
        </div>

        <!-- Modal Footer -->
        <div class="flex justify-end pt-4 border-t mt-4">
            <button id="closeModalBtn" class="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                Close
            </button>
        </div>
    </div>
</div>

<script>
// Security Details Modal Handler
document.getElementById('securityDetailsBtn').addEventListener('click', async function() {
    const modal = document.getElementById('securityModal');
    const content = document.getElementById('securityContent');

    // Show modal
    modal.classList.remove('hidden');

    // Fetch security analysis
    try {
        const response = await fetch('/sensors/security-analysis');
        const result = await response.json();

        if (result.status === 'ok') {
            const data = result.data;
            content.innerHTML = renderSecurityReport(data);
        } else {
            content.innerHTML = `
                <div class="max-w-2xl mx-auto text-center py-12">
                    <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L5.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                    <h3 class="text-xl font-bold text-gray-900 mb-2">Flask Scanner Backend Required</h3>
                    <p class="text-red-600 mb-4">${result.message}</p>
                    ${result.help ? `
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
                            <p class="text-sm font-semibold text-blue-900 mb-2">💡 How to fix:</p>
                            <p class="text-sm text-blue-800 mb-2">Open a terminal and run:</p>
                            <code class="block bg-gray-900 text-green-400 p-3 rounded font-mono text-sm">
                                cd mqtt-scanner<br>
                                python app.py
                            </code>
                            <p class="text-xs text-blue-700 mt-2">The Flask server should start on port 5000</p>
                        </div>
                    ` : ''}
                </div>
            `;
        }
    } catch (error) {
        content.innerHTML = `
            <div class="text-center py-8">
                <p class="text-red-600">Error: ${error.message}</p>
            </div>
        `;
    }
});

// Close modal handlers
document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('securityModal').classList.add('hidden');
});

document.getElementById('closeModalBtn').addEventListener('click', () => {
    document.getElementById('securityModal').classList.add('hidden');
});

// Close on outside click
document.getElementById('securityModal').addEventListener('click', (e) => {
    if (e.target.id === 'securityModal') {
        document.getElementById('securityModal').classList.add('hidden');
    }
});

// Render security report
function renderSecurityReport(data) {
    const secureBroker = data.secure_broker;
    const insecureBroker = data.insecure_broker;

    return `
        <!-- Port Comparison -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            ${renderBrokerCard(insecureBroker, 'Insecure Port (1883)', 'red')}
            ${renderBrokerCard(secureBroker, 'Secure Port (8883)', 'green')}
        </div>

        <!-- Detailed Report for Insecure Port -->
        ${insecureBroker.available ? renderDetailedReport(insecureBroker, 'Insecure Port (1883)') : ''}

        <!-- Detailed Report for Secure Port -->
        ${secureBroker.available ? renderDetailedReport(secureBroker, 'Secure Port (8883)') : ''}
    `;
}

// Render broker comparison card
function renderBrokerCard(broker, title, color) {
    if (!broker.available) {
        return `
            <div class="bg-gray-50 rounded-lg p-6 border-2 border-gray-300">
                <h4 class="text-lg font-bold mb-4">${title}</h4>
                <p class="text-gray-600">Broker not scanned or not available</p>
            </div>
        `;
    }

    const riskColor = {
        'CRITICAL': 'red',
        'HIGH': 'orange',
        'MEDIUM': 'yellow',
        'LOW': 'green',
        'UNKNOWN': 'gray'
    }[broker.risk_level] || 'gray';

    return `
        <div class="bg-${color}-50 rounded-lg p-6 border-2 border-${color}-300">
            <div class="flex justify-between items-start mb-4">
                <h4 class="text-lg font-bold text-${color}-900">${title}</h4>
                <span class="px-3 py-1 bg-${riskColor}-600 text-white text-xs font-bold rounded-full">
                    ${broker.risk_level}
                </span>
            </div>

            <div class="space-y-3">
                <div class="flex items-center">
                    <span class="text-sm font-medium text-gray-600 w-32">IP Address:</span>
                    <span class="text-sm text-gray-900">${broker.ip}:${broker.port}</span>
                </div>
                <div class="flex items-center">
                    <span class="text-sm font-medium text-gray-600 w-32">TLS/SSL:</span>
                    <span class="text-sm">${broker.tls_enabled ? '✅ Enabled' : '❌ Disabled'}</span>
                </div>
                <div class="flex items-center">
                    <span class="text-sm font-medium text-gray-600 w-32">Publishers:</span>
                    <span class="text-sm text-gray-900">${broker.publisher_count}</span>
                </div>
                <div class="flex items-center">
                    <span class="text-sm font-medium text-gray-600 w-32">Subscribers:</span>
                    <span class="text-sm text-gray-900">${broker.subscriber_count}</span>
                </div>
                <div class="flex items-center">
                    <span class="text-sm font-medium text-gray-600 w-32">Active Topics:</span>
                    <span class="text-sm text-gray-900">${broker.topic_count}</span>
                </div>
            </div>
        </div>
    `;
}

// Render detailed security report
function renderDetailedReport(broker, title) {
    const riskEmoji = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢',
        'UNKNOWN': '⚪'
    }[broker.risk_level] || '⚪';

    return `
        <div class="bg-white border-2 border-gray-200 rounded-lg p-6 mb-6">
            <h3 class="text-xl font-bold mb-6 pb-3 border-b-2">
                📋 Detailed Report: ${title}
            </h3>

            <!-- Target Information -->
            <div class="mb-6">
                <h4 class="text-lg font-semibold mb-3 flex items-center">
                    📍 TARGET INFORMATION
                </h4>
                <div class="bg-gray-50 rounded p-4 space-y-2 font-mono text-sm">
                    <div><span class="font-bold">IP Address:</span> ${broker.ip}</div>
                    <div><span class="font-bold">Port:</span> ${broker.port} ${broker.tls_enabled ? '(Secure MQTT with TLS)' : '(Insecure MQTT)'}</div>
                    <div><span class="font-bold">Result:</span> ${broker.result}</div>
                    <div><span class="font-bold">Classification:</span> ${broker.classification}</div>
                    <div><span class="font-bold">Timestamp:</span> ${new Date(broker.timestamp).toLocaleString()}</div>
                </div>
            </div>

            <!-- Security Assessment -->
            <div class="mb-6">
                <h4 class="text-lg font-semibold mb-3">🔒 SECURITY ASSESSMENT</h4>
                <div class="bg-${broker.risk_level === 'CRITICAL' || broker.risk_level === 'HIGH' ? 'red' : broker.risk_level === 'MEDIUM' ? 'yellow' : 'green'}-100 rounded p-4">
                    <div class="text-lg font-bold mb-3">Risk Level: ${riskEmoji} ${broker.risk_level}</div>

                    ${broker.security_issues.length > 0 ? `
                        <div class="mt-4">
                            <div class="font-semibold mb-2">⚠️ Security Issues Found:</div>
                            <ul class="list-disc list-inside space-y-1">
                                ${broker.security_issues.map(issue => `<li>${issue}</li>`).join('')}
                            </ul>
                        </div>
                    ` : '<p class="text-green-700">No major security issues detected.</p>'}

                    ${broker.recommendations.length > 0 ? `
                        <div class="mt-4">
                            <div class="font-semibold mb-2">💡 Recommendations:</div>
                            <ul class="list-none space-y-1">
                                ${broker.recommendations.map(rec => `<li>✓ ${rec}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>

            <!-- Access Control -->
            <div class="mb-6">
                <h4 class="text-lg font-semibold mb-3">🛡️ ACCESS CONTROL</h4>
                <div class="bg-gray-50 rounded p-4 space-y-2">
                    <div><span class="font-bold">Anonymous Access:</span> ${broker.classification === 'open_or_auth_ok' ? '❌ ALLOWED (Security Risk!)' : '✅ BLOCKED'}</div>
                    <div><span class="font-bold">Authentication:</span> ${broker.classification === 'not_authorized' ? '✅ Required' : '❌ Not Required'}</div>
                    <div><span class="font-bold">Port Type:</span> ${broker.tls_enabled ? '🔒 Secure (TLS/SSL)' : '⚠️ Insecure (Plain)'}</div>
                </div>
            </div>

            <!-- Publishers -->
            ${broker.publisher_count > 0 ? `
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">📤 DETECTED PUBLISHERS (${broker.publisher_count})</h4>
                    <div class="space-y-3">
                        ${broker.publishers.slice(0, 10).map((pub, idx) => `
                            <div class="bg-blue-50 rounded p-3 border border-blue-200">
                                <div class="font-semibold text-blue-900">${idx + 1}. Topic: ${pub.topic || 'Unknown'}</div>
                                <div class="text-sm text-gray-700 mt-1">
                                    Payload Size: ${pub.payload_size || 'N/A'} bytes |
                                    QoS: ${pub.qos || 0} |
                                    Retained: ${pub.retained ? 'Yes' : 'No'}
                                </div>
                                ${pub.note ? `<div class="text-xs text-gray-600 mt-1">Note: ${pub.note}</div>` : ''}
                            </div>
                        `).join('')}
                        ${broker.publisher_count > 10 ? `<p class="text-sm text-gray-600">... and ${broker.publisher_count - 10} more</p>` : ''}
                    </div>
                </div>
            ` : ''}

            <!-- Subscribers -->
            ${broker.subscriber_count > 0 ? `
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">📥 DETECTED SUBSCRIBERS (${broker.subscriber_count})</h4>
                    <div class="space-y-2">
                        ${broker.subscribers.slice(0, 10).map((sub, idx) => `
                            <div class="bg-purple-50 rounded p-3 border border-purple-200">
                                <div class="font-semibold text-purple-900">${idx + 1}. Client ID: ${sub.client_id || 'Unknown'}</div>
                                ${sub.note ? `<div class="text-xs text-gray-600 mt-1">Note: ${sub.note}</div>` : ''}
                                ${sub.detected_via ? `<div class="text-xs text-gray-600">Detected via: ${sub.detected_via}</div>` : ''}
                            </div>
                        `).join('')}
                        ${broker.subscriber_count > 10 ? `<p class="text-sm text-gray-600">... and ${broker.subscriber_count - 10} more</p>` : ''}
                    </div>
                </div>
            ` : ''}

            <!-- Active Topics -->
            ${broker.topic_count > 0 ? `
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">📋 ACTIVE TOPICS DISCOVERED (${broker.topic_count})</h4>
                    <div class="bg-gray-50 rounded p-4">
                        <ul class="list-disc list-inside space-y-1">
                            ${broker.topics.map(topic => `<li class="font-mono text-sm">${topic}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            ` : ''}

            <!-- Certificate Info -->
            ${broker.tls_enabled ? `
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">📜 CERTIFICATE INFO</h4>
                    <div class="bg-gray-50 rounded p-4">
                        <pre class="text-xs font-mono whitespace-pre-wrap">${broker.cert_info}</pre>
                    </div>
                </div>
            ` : `
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">📜 CERTIFICATE INFO</h4>
                    <div class="bg-red-50 rounded p-4 text-red-700">
                        ⚠️ Not a TLS port - No certificate information available
                    </div>
                </div>
            `}
        </div>
    `;
}
</script>
