import React from 'react'
import {Link} from "react-router-dom";

export function AnnotatedTree({tree, selected_category, key_ = 0}) {

    return <ul key={key_.toString()}>
        {tree.map((node, i) => (
            <li key={`${key_}-${i}`} className={selected_category.slug === node.category.slug ? "active" : undefined}>
                <Link to={`/category/${node.category.slug}`}>{node.category.category}({node.category.products_count__sum})
                </Link>
                {
                    node.children !== null &&
                    <AnnotatedTree tree={node.children} selected_category={selected_category} key_={key_ + 1}/>
                }
            </li>
        ))}
    </ul>
}