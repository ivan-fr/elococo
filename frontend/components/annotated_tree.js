import React from 'react'
import Link from 'next/link'
import PropTypes from 'prop-types';

export function AnnotatedTree({ tree, selected_category }) {

    return <ul>
        {tree.map((node, i) => (
            <>
                <li key={i} className={selected_category.slug == node.category.slug ? "active" : ""}>
                    <Link href="/"><a>{node.category.category}({node.category.products_count__sum})</a></Link>
                </li>
                {node.children !== null && <AnnotatedTree tree={node.children} selected_category={selected_category} />}
            </>
        ))}
    </ul>
}

AnnotatedTree.propTypes = {
    tree: PropTypes.array.isRequired,
    selected_category: PropTypes.object.isRequired
}
