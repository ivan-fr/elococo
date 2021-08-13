import React from 'react'
import Footer from './footer';
import NavBar from './navbar';
import Head from 'next/head';
import Image from 'next/image';

function Base({ children }) {
    return <>
        <Head>
            <title>Create Next App</title>
            <meta name="description" content="Generated by create next app" />
            <link rel="icon" href="/favicon.ico" />
        </Head>
        <div className="wrapper">
            <figure id="main_logo">
                <Image src='/logo.png' width={350} height={120} alt="logo" />
            </figure>
            <NavBar />

            <main className="gridded">
                <div className="main">
                    {children}
                </div>
            </main>
        </div>

        <Footer />
    </>
}

export default Base;