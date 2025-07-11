import dynamic from 'next/dynamic'

const IDEWithNoSSR = dynamic(
  () => import('./IDE').then(mod => mod.IDE),
  { ssr: false }
)

export default IDEWithNoSSR
