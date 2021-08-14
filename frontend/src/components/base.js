import React from 'react'
import logo from '../public/logo.png'
import Footer from './footer';
import NavBar from './navbar';
import {
    BrowserRouter,
    Switch,
    Route
} from 'react-router-dom'
import Catalogue from './catalogue';
import Product from "./product";

function Base() {
    return <BrowserRouter>
        <div className="wrapper">
            <figure id="main_logo">
                <img src={logo} alt="logo" />
            </figure>
            <NavBar />

            <main className="gridded">
                <div className="main">
                    <Switch>
                        <Route exact path="/" component={Catalogue} />
                        <Route path="/catalogue/:slug" component={Product} />
                        <Route path="/category/:slug" component={Catalogue} />
                    </Switch>
                </div>
            </main>
        </div>

        <Footer />
    </BrowserRouter>
}

export default Base;
