import paths from "../api_urls"

export function getUrlSearchParams(urlParsedQuery) {
    let str = '?';

    for (const key in urlParsedQuery) {
        str += `${key}=${urlParsedQuery[key]}&`
    }

    if (urlParsedQuery.lenght === 0) {
        str = ''
    }

    return new URLSearchParams(str.slice(0, -1))
}

export function get_route_with_args(route_name, args = []) {
    return get_path_with_args(paths.route[route_name]['url'], args)
}

export function get_path_with_args(path, args = []) {
    let path_to_transform = path
    for (const arg of args) {
        path_to_transform = path_to_transform.replace(new RegExp("<[^<>]+>(.*)"), `${arg}$1`)
    }

    return path_to_transform
}

export function get_url(path, urlParsedQuey=null) {
    let url = new URL(path, paths.origin, false)
    url.searchParams.set("format", "json")

    if (urlParsedQuey == null) {
        return url
    }
    
    const urlSearchParams = getUrlSearchParams(urlParsedQuey)
    
    for (const pair of urlSearchParams.entries()) {
        url.searchParams.set(pair[0], pair[1])
    }

    return url
}
