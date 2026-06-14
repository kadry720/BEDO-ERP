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

export function routePath(value: string) {
  return decodedRouteParam(value)
    .split("/")
    .filter(Boolean)
    .map((part) => routeSegment(part))
    .join("/");
}

export function projectRoute(scope: "gm" | "srs", project: string, suffix = "") {
  return `/${scope}/projects/${routeSegment(project)}${suffix}`;
}

export function trainerItemRoute(scope: "gm" | "srs", project: string, trainerItem: string) {
  return `${projectRoute(scope, project)}/items/${routeSegment(trainerItem)}`;
}

export function projectWorkflowRoute(scope: "gm" | "srs" | "command-center", project: string, suffix = "") {
  return `/${scope}/project/${routePath(project)}${suffix}`;
}

export function trainerItemWorkflowRoute(scope: "gm" | "srs" | "command-center", project: string, trainerItem: string) {
  return `${projectWorkflowRoute(scope, project)}/items/${routeSegment(trainerItem)}`;
}

function splitQueryAndHash(value: string) {
  const match = value.match(/^([^?#]*)([?#].*)?$/);
  return { pathname: match?.[1] || value, suffix: match?.[2] || "" };
}

export function normalizeProjectActionUrl(actionUrl: string) {
  if (!actionUrl.startsWith("/")) return actionUrl;

  const { pathname, suffix } = splitQueryAndHash(actionUrl);
  for (const scope of ["gm", "srs", "command-center"] as const) {
    const prefixes = [`/${scope}/project/`, `/${scope}/projects/`];
    const prefix = prefixes.find((candidate) => pathname.startsWith(candidate));
    if (!prefix) continue;

    const tail = pathname.slice(prefix.length);
    const itemMarker = "/items/";
    const itemIndex = tail.indexOf(itemMarker);
    if (itemIndex >= 0) {
      const project = tail.slice(0, itemIndex);
      const trainerItem = tail.slice(itemIndex + itemMarker.length);
      return `${trainerItemWorkflowRoute(scope, project, trainerItem)}${suffix}`;
    }

    const trainersMarker = "/trainers";
    if (tail.endsWith(trainersMarker)) {
      const project = tail.slice(0, -trainersMarker.length);
      return `${projectWorkflowRoute(scope, project, trainersMarker)}${suffix}`;
    }

    return `${projectWorkflowRoute(scope, tail)}${suffix}`;
  }

  return actionUrl;
}
