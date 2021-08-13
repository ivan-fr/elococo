import Catalogue from '../components/catalogue'
import {get_route_with_args, get_url} from '../utils/url'

export default function Home({data}) {
  return (
    <Catalogue response={data} />
  )
}

export async function getServerSideProps(context) {
  const path = get_route_with_args('catalogue_api:product-list', [])
  const url = get_url(path, context.query)
  const res = await fetch(url.href)
  const data = await res.json()

  return { props: { data } }
}
