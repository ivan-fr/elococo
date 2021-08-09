import React from 'react'
import Base from './components/base'
import "./css/design.css"
import PathsContext from "./contexts/paths"

function App() {
  return (
    <PathsContext.Provider>
      <Base />
    </PathsContext.Provider>
  );
}

export default App;
