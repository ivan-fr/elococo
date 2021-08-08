import React from 'react'
import Base from './components/base'
import  { 
  BrowserRouter, 
  Switch, 
  Route 
} from 'react-router-dom'
import "./css/design.css"

function App() {
  return (
    <>
    <BrowserRouter>
      <Switch>
        <Route exact path="/" component={Base}/>
        <Route component={Base}/>
      </Switch>
    </BrowserRouter>
    </>
  );
}

export default App;
