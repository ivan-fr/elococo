import { useEffect, useContext, useState } from 'react';
import { PathsContext, OriginUrlContext } from '../contexts/paths';
import { get_path_with_args, get_url } from '../utils/url';

export function useSimpleFetch(route_name, args, urlSearchParams=null) {
    const paths_data = useContext(PathsContext)
    const origin = useContext(OriginUrlContext)

    const [response, setResponse] = useState({ 'isLoading': null, 'data': null, 'error': null })

    useEffect(() => {
        const path = get_path_with_args(paths_data[route_name]['url'], args)
        const url = get_url(origin, path, urlSearchParams)

        setResponse(
            r => {
                return { ...r, 'isLoading': true }
            }
        )
        fetch(
            url.href
        ).then(result => result.json())
            .then((result) => {
                setResponse(
                    r => {
                        return { ...r, 'isLoading': false, 'data': result }
                    }
                )
            }, (error) => {
                setResponse(
                    r => {
                        return { ...r, 'isLoading': false, 'error': error }
                    }
                )
            })
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [route_name]);

    return response
}