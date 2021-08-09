import React from 'react'
import logo from '../images/logo.png'
import Footer from './footer';
import NavBar from './navbar';
import {
    BrowserRouter,
    Switch,
    Route
} from 'react-router-dom'
import Catalogue from './catalogue';

function Base() {
    return <>
        <div className="wrapper">
            <figure id="main_logo">
                <img src={logo} alt="logo" />
            </figure>
            <NavBar />

            <main className="gridded">
                <div className="main">
                    <BrowserRouter>
                        <Switch>
                            <Route exact path="/" component={Catalogue} />
                            <Route component={Catalogue} />
                        </Switch>
                    </BrowserRouter>
                </div>
            </main>
        </div>

        <Footer />
    </>
}

export default Base;
