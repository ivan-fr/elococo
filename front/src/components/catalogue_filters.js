import React, {useCallback, useMemo} from 'react';
import {useNavigate, useLocation} from "react-router-dom";

function CatalogueOrder() {
    const history = useNavigate()
    const {search} = useLocation()
    const query = useMemo(() => new URLSearchParams(search), [search]);

    const onClickOrder = useCallback(
        (e, order) => {
            e.preventDefault()
            query.set('order', order)
            history({search: '?' + query.toString()})
        }, [query, history]
    )

    const order = useMemo(() => {
        const order = query.get('order')

        switch (order) {
            case "desc":
                return order
            case "asc":
                return order
            default:
                return null
        }
    }, [query])

    return <nav className="order_filters">
        <ul>
            <li className={order && order === "asc" ? "is-active" : undefined}>
                <a href="/" onClick={(e) => onClickOrder(e, "asc")}>
                    Prix croissant
                </a>
            </li>
            <li className={order && order === "desc" ? "is-active" : undefined}>
                <a href="/" onClick={(e) => onClickOrder(e, "desc")}>
                    Prix décroissant
                </a>
            </li>
            <li className={order === null ? "is-active" : undefined}>
                <a href="/" onClick={(e) => onClickOrder(e, null)}>
                    Derniers ajouts
                </a>
            </li>
        </ul>
    </nav>
}

export default CatalogueOrder;
