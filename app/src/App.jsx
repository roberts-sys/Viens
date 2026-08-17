import { motion } from 'framer-motion'

function App() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      style={{ padding: 40, fontFamily: 'sans-serif' }}
    >
      <h1>Framer Motion is wired up</h1>
      <p>Build new components here, then port them into the static site.</p>
    </motion.div>
  )
}

export default App
