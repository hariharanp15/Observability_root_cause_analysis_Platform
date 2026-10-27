import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
import '../styles.css';
const links = [['/', 'Overview'], ['/ingest', 'Ingest'], ['/traces', 'Traces'], ['/dependencies', 'Map'], ['/logs', 'Logs'], ['/metrics', 'Metrics'], ['/diagnostics', 'RCA'], ['/alerts', 'Alerts']];
export default function Layout({ children }) { return _jsxs(_Fragment, { children: [_jsxs("header", { children: [_jsx(Link, { className: "brand", to: "/", children: "OBSERVE" }), _jsx("nav", { children: links.map(([p, n]) => _jsx(Link, { to: p, children: n }, p)) })] }), _jsx("main", { children: children })] }); }
