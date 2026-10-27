import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import api from '../api/client';
const now = new Date().toISOString();
const templates = { trace: { event_id: 'trace-event-001', trace_id: 'trace-001', span_id: 'span-001', parent_span_id: null, service_name: 'order-service', operation_name: 'create_order', start_time: now, end_time: now, status: 'OK', error_message: null }, log: { event_id: 'log-event-001', service_name: 'order-service', message: 'Order created', severity: 'INFO', timestamp: now, trace_id: 'trace-001', span_id: 'span-001' }, metric: { event_id: 'metric-event-001', service_name: 'order-service', metric_name: 'request_latency_ms', metric_value: 125, recorded_at: now }, batch: { traces: [], logs: [], metrics: [] } };
export default function Ingestion() { const [kind, setKind] = useState('trace'); const [body, setBody] = useState(JSON.stringify(templates.trace, null, 2)); const [result, setResult] = useState(''); const choose = (v) => { setKind(v); setBody(JSON.stringify(templates[v], null, 2)); setResult(''); }; const send = () => { try {
    api.post(`/telemetry/${kind === 'batch' ? 'batch' : kind + 's'}`, JSON.parse(body)).then(r => setResult(`Accepted: ${JSON.stringify(r.data.data)}`)).catch(e => setResult(`Request failed: ${e.response?.data?.detail || e.message}`));
}
catch {
    setResult('Invalid JSON payload.');
} }; return _jsxs(_Fragment, { children: [_jsx("h1", { children: "Telemetry ingestion" }), _jsx("p", { children: "Post validated events directly to the ingestion API." }), _jsx("div", { className: "buttons", children: Object.keys(templates).map(x => _jsx("button", { className: kind === x ? 'selected' : '', onClick: () => choose(x), children: x }, x)) }), _jsx("textarea", { value: body, onChange: e => setBody(e.target.value), spellCheck: false }), _jsx("p", { children: _jsxs("button", { onClick: send, children: ["POST /telemetry/", kind === 'batch' ? 'batch' : kind + 's'] }) }), result && _jsx("pre", { className: "result", children: result })] }); }
