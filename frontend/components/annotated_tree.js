import React from 'react'
import Link from 'next/link'
import PropTypes from 'prop-types';

export function AnnotatedTree({tree, selected_category, key_ = 0}) {

    return <ul key={key_.toString()}>
        {tree.map((node, i) => (
            <li key={`${key_}-${i}`} className={selected_category.slug === node.category.slug ? "active" : undefined}>
                <Link
                    href={`/category/${node.category.slug}`}><a>{node.category.category}({node.category.products_count__sum})
                </a>
                </Link>
                {
                    node.children !== null &&
                    <AnnotatedTree tree={node.children} selected_category={selected_category} key_={key_ + 1}/>
                }
            </li>
        ))}
    </ul>
}

AnnotatedTree.propTypes = {
    tree: PropTypes.array.isRequired,
    selected_category: PropTypes.object.isRequired
}
