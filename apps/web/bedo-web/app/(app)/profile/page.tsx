import { ProfileForm } from "@/features/auth/ProfileForm";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

type Profile = {
  user: string;
  username: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  email: string;
  phone_number: string;
};

export default async function Page() {
  const session = await requireSession();
  const profile = await frappeCall<Profile>("bedo_platform.api.web.get_my_profile", {}, session.user);
  return <ProfileForm profile={profile} session={session} />;
}
