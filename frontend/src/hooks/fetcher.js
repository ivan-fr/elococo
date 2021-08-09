import { useEffect, useContext } from 'react';
import { PathsContext, OriginUrlContext } from '../contexts/paths';
import { get_path_with_args, get_url } from '../utils/url';

export function useSimpleFetch(route_name, args, setData, setError, setIsLoading = null) {
    const paths_data = useContext(PathsContext)
    const origin = useContext(OriginUrlContext)

    useEffect(() => {
        const path = get_path_with_args(paths_data[route_name], args)
        const url = get_url(origin, path)
        
        setIsLoading(true)
        fetch(
            url.pathname + url.search
        ).then(result => result.json())
        .then((result) => {
            setIsLoading(false)
            setData(result)
        }, (error) => {
            setIsLoading(false);
            setError(error);
        })
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [args, route_name]);
}