/* dsh-splash-fish — host half.
 *
 * The whole film lives in the client half (client.js), mounted on the
 * `shell.overlay` slot. This host half is a deliberate no-op: it exists so the
 * loader mounts a fiber for the package, which is what lets the client bundle
 * run in the page.
 */

/** Stable Cordis plugin name; matches cordis.patch.yml's roster id. */
const name = "dsh-splash-fish";

/** No host-side services or registries are required. */
function apply() {}

export { apply, name };
