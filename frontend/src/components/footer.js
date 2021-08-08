import React from 'react'
import logo from '../images/logo.png'
import rule2 from '../images/rule2.bmp'
import visa1 from '../images/visa1.png'
import master from '../images/master.png'
import cb from '../images/cb.svg'

class Footer extends React.Component {
    render() {
        return <footer>
        <section className="logos">
            <h3>Logos</h3>
            <figure>
                <img src={logo} alt="logo" />
            </figure>
            <div>
            </div>
        </section>
        <section>
            <h3>Nos engagements</h3>
            <ul>
                <li>Livraison offerte dès €</li>
                <li>Paiement 100% sécurisé</li>
                <li>Articles en stock</li>
            </ul>
        </section>
        <section>
            <h3>À Propos</h3>
            <p>Développé par <a target="_blank" href="{% url 'ivan_cv' %}">BESEVIC Ivan</a>.</p>
            <p> Tous droits réservés. .</p>
            <p>Ceci est un site de démonstration.</p>
            <figure>
                <a target="_blank" rel="noreferrer" href="https://creativecommons.org/licenses/by-nc-nd/4.0/">
                    <img src={rule2} alt="licence" />
                </a>
            </figure>
        </section>
        <section>
            <h3>
                Mode de paiements
            </h3>
            <div className="payments_mode">
                <figure>
                    <img src={visa1} alt="visa"/>
                </figure>
                <figure>
                    <img src={master} alt="master"/>
                </figure>
                <figure>
                    <img src={cb} alt="carte bleue"/>
                </figure>
            </div>
        </section>
    </footer>
    }
}

export default Footer;
