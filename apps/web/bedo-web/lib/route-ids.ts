export function decodedRouteParam(value: string) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function routeSegment(value: string) {
  return encodeURIComponent(decodedRouteParam(value));
}

export function projectRoute(scope: "gm" | "srs", project: string, suffix = "") {
  return `/${scope}/projects/${routeSegment(project)}${suffix}`;
}

export function trainerItemRoute(scope: "gm" | "srs", project: string, trainerItem: string) {
  return `${projectRoute(scope, project)}/items/${routeSegment(trainerItem)}`;
}

function splitQueryAndHash(value: string) {
  const match = value.match(/^([^?#]*)([?#].*)?$/);
  return { pathname: match?.[1] || value, suffix: match?.[2] || "" };
}

export function normalizeProjectActionUrl(actionUrl: string) {
  if (!actionUrl.startsWith("/")) return actionUrl;

  const { pathname, suffix } = splitQueryAndHash(actionUrl);
  for (const scope of ["gm", "srs"] as const) {
    const prefix = `/${scope}/projects/`;
    if (!pathname.startsWith(prefix)) continue;

    const tail = pathname.slice(prefix.length);
    const itemMarker = "/items/";
    const itemIndex = tail.indexOf(itemMarker);
    if (itemIndex >= 0) {
      const project = tail.slice(0, itemIndex);
      const trainerItem = tail.slice(itemIndex + itemMarker.length);
      return `${trainerItemRoute(scope, project, trainerItem)}${suffix}`;
    }

    const trainersMarker = "/trainers";
    if (tail.endsWith(trainersMarker)) {
      const project = tail.slice(0, -trainersMarker.length);
      return `${projectRoute(scope, project, trainersMarker)}${suffix}`;
    }

    return `${projectRoute(scope, tail)}${suffix}`;
  }

  return actionUrl;
}
