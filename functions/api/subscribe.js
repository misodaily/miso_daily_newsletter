
export async function onRequestPost({ request, env }) {
    try {
        const formData = await request.formData();
        const email = formData.get("email");
        const channel = formData.get("channel");
        const marketingConsent = formData.get("marketing_consent") === "on";

        if (!email) {
            return new Response("Email is required", { status: 400 });
        }

        // Insert into D1 Database
        // Note: 'DB' matches the binding name in wrangler.jsonc
        const info = await env.DB.prepare(
            "INSERT INTO subscribers (email, channel, marketing_consent, created_at) VALUES (?, ?, ?, ?)"
        )
            .bind(email, channel, marketingConsent ? 1 : 0, new Date().toISOString())
            .run();

        if (info.success) {
            // Redirect to a thank you page or show success message
            return new Response("구독이 완료되었습니다! 감사합니다. 🍊", {
                headers: { "Content-Type": "text/html; charset=utf-8" },
            });
        } else {
            return new Response("Database Error", { status: 500 });
        }
    } catch (e) {
        return new Response(`Error: ${e.message}`, { status: 500 });
    }
}
