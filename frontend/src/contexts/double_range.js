import React from 'react'

export const onChange = (doubleRange, history, query) => {
    return ({ name, value }) => {

    switch (name) {
        case 'min':
            query.set(doubleRange.kwargs_min, value)
            break;
        case 'max':
            query.set(doubleRange.kwargs_max, value)
            break;
        default:
            break;
    }

    history.push({
        search: `?${query.toString()}`
    })
}}

export const doubleRangeContext = React.createContext(
    {'min_base': null, 'max_base': null, 'kwargs_min': 'min_ttc_price', 'kwargs_max': 'max_ttc_price'}
)
