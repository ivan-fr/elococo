import React from 'react'
import Image from 'next/image'


function Footer() {
    return <footer>
        <section className="logos">
            <h3>Logos</h3>
            <figure>
                <Image src={'/logo.png'}  width={400} height={150} alt="logo" />
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
                    <Image src={'/rule2.bmp'} alt="licence"  width={50} height={50} />
                </a>
            </figure>
        </section>
        <section>
            <h3>
                Mode de paiements
            </h3>
            <div className="payments_mode">
                <figure>
                    <Image src='/visa1.png' width={70} height={70} alt="visa" />
                </figure>
                <figure>
                    <Image src='/master.png' width={70} height={70} alt="master" />
                </figure>
                <figure>
                    <Image src='/cb.svg' width={70} height={70} alt="carte bleue" />
                </figure>
            </div>
        </section>
    </footer>
}

export default Footer;
