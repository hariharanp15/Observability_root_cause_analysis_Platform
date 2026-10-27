import {Link} from 'react-router-dom'; import '../styles.css';
const links=[['/','Overview'],['/ingest','Ingest'],['/traces','Traces'],['/dependencies','Map'],['/logs','Logs'],['/metrics','Metrics'],['/diagnostics','RCA'],['/alerts','Alerts']];
export default function Layout({children}:{children:React.ReactNode}){return <><header><Link className="brand" to="/">OBSERVE</Link><nav>{links.map(([p,n])=><Link to={p} key={p}>{n}</Link>)}</nav></header><main>{children}</main></>}
