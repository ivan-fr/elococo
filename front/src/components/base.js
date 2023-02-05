import React from 'react'
import logo from '../public/logo.png'
import Footer from './footer';
import NavBar from './navbar';
import {BrowserRouter, Route, Routes} from 'react-router-dom'
import Catalogue from './catalogue';
import Product from "./product";
import Basket from "./basket";
import Order, {Checkout} from "./order";

function Base() {
    return <BrowserRouter>
        <div className="wrapper">
            <figure id="main_logo">
                <img src={logo} alt="logo"/>
            </figure>
            <NavBar/>

            <main className="gridded">
                <div className="main">
                    <Routes>
                        <Route exact path="/" element={<Catalogue/>}/>
                        <Route path="/basket" element={<Basket/>}/>
                        <Route path="/order" element={<Order/>}/>
                        <Route path="/checkout" element={<Checkout/>}/>
                        <Route path="/catalogue/:slug" element={<Product/>}/>
                        <Route path="/category/:slug" element={<Catalogue/>}/>
                    </Routes>
                </div>
            </main>
        </div>

        <Footer/>
    </BrowserRouter>
}

export default Base;
