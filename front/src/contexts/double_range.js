import React from 'react'

export const doubleRangeContext = React.createContext(
    {'min_base': null, 'max_base': null, 'kwargs_min': 'min_ttc_price', 'kwargs_max': 'max_ttc_price'}
)
