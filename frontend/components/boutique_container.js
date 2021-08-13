import React, {useMemo} from 'react'
import Link from 'next/link'
import Image from 'next/image'
import {AnnotatedTree} from './annotated_tree'


function BoutiqueContainer({response}) {
    let results = useMemo(() => {
        return response?.results
    }, [response])

    return <>
        <div id="boutique-container" className={results?.filter_list && "with_filters"}>
            <div id="boutique">
                {results?.related_products && results.related_products.map((product, i) => (
                    <article key={i}>
                        <h3>{product.name}</h3>

                        <figure className="hover_figure">
                            <Link href="/"><a>
                                <Image layout='fill' src={product.productimage_set[0].image}
                                       alt={'product' + i}/>

                                {product.effective_reduction > 0 &&
                                <div className="info_reduction">
                                    -{product.effective_reduction}%
                                </div>
                                }
                                <div className="info_price">
                                    {product.price_exact_ttc}€ TTC
                                </div>
                                <figcaption>
                                    {product.name}
                                </figcaption>
                            </a>
                            </Link>
                        </figure>
                    </article>
                ))}
            </div>

            {results?.filter_list && (
                <section className="product_categories_right">
                    <h2>Filtres associés</h2>
                    <AnnotatedTree tree={results.filter_list} selected_category={results.selected_category}/>
                </section>
            )}
        </div>
        {(response?.next || response?.previous) && <nav id="boutique_pagination">
            <ul className="pagination">
                {response?.previous && <>
                    <li className="page-item">
                        <span className="page-link">
                            <Link href="/">
                                Prec
                            </Link>
                        </span>
                    </li>
                </>}
                {response?.next && <>
                    <li className="page-item">
                        <span className="page-link">
                            <Link href="/">
                                Suiv
                            </Link>
                        </span>
                    </li>
                </>}
            </ul>
        </nav>}
    </>
}

export default BoutiqueContainer;
