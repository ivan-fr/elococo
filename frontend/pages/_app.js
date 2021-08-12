import Base from "../components/base"
import '../styles/design.css'
import "../styles/double_range.css"

function MyApp({ Component, pageProps }) {
  return <Base>
    <Component {...pageProps} />
  </Base>
}

export default MyApp
