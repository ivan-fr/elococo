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

export function get_path_with_args(path, args = []) {
    let path_to_transform = path
    for (const arg of args) {
        path_to_transform = path_to_transform.replace(new RegExp("<[^<>]+>(.*)"), `${arg}$1`)
    }

    return path_to_transform
}

export function get_url(origin, path, urlParsedQuey=null) {
    let url = new URL(path, origin)
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
