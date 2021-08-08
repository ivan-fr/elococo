import React from 'react'
import logo from '../images/logo.png'
import Footer from './footer';
import NavBar from './navbar';

class Base extends React.Component {
    render() {
        return <>
            <div className="wrapper">
                <figure id="main_logo">
                    <img src={logo} alt="logo" />
                </figure>
                <NavBar />

                <main className="gridded">
                    <div className="main">

                    </div>
                </main>
            </div>

            <Footer />
        </>
    }
}

export default Base;
