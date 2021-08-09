export function get_path_with_args(path, args = []) {
    let path_to_transform = path
    for (const arg of args) {
        path_to_transform = path_to_transform.replace(new RegExp("<[^<>]+>(.*)"), `${arg}$1`)
    }

    return path_to_transform
}

export function get_url(origin, path) {
    let url = new URL(path, origin)
    url.searchParams.set("format", "json")
    return url
}
