import React from 'react'
import paths from "../api_urls"

export const PathsContext = React.createContext(paths)
export const OriginUrlContext = React.createContext('http://127.0.0.1:8000')
