import json, os, time, requests
from pathlib import Path

home = Path.home()
cred_path = home / '.config/43farm/credentials.json'
state_path = home / '.config/43farm/state.json'
local_skill = home / '.hermes/skills/43farm'

with open(cred_path) as f:
    token = json.load(f)['farmToken']

with open(state_path) as f:
    state = json.load(f)

API_BASE = 'https://farm.43chat.cn/trpc'
headers = {'X-Farm-Token': token}

def api(path, method='GET', data=None, params=None):
    url = f"{API_BASE}/{path}"
    if method == 'GET':
        r = requests.get(url, headers=headers, params=params, timeout=30)
    else:
        r = requests.post(url, headers=headers, json=(data if data is not None else {}), timeout=30)
    return r

now = int(time.time())
reports = []

def save_state():
    with open(state_path, 'w') as f:
        json.dump(state, f)

msg_due = now - state.get('lastMessageCheck', 0) >= 1800
ver_due = now - state.get('lastVersionCheck', 0) >= 7200

if msg_due:
    resp = api('farm.events.poll')
    try:
        events_data = resp.json()
    except Exception as e:
        reports.append(f"events.poll 解析失败: {e}, 状态={resp.status_code}, 内容={resp.text[:200]}")
        events_data = {}

    if isinstance(events_data, dict) and 'error' in events_data:
        reports.append(f"events.poll 错误: {events_data['error']}")
    else:
        events = events_data.get('result', {}).get('data', {}).get('events', [])
        event_ids = []
        mature_or_wilted = False
        for ev in events:
            etype = ev.get('type')
            payload = ev.get('payload', {})
            event_ids.append(ev.get('id'))
            if etype in ('CROP_MATURE', 'CROP_WILTED'):
                mature_or_wilted = True
            elif etype == 'CROP_STOLEN':
                items = payload.get('items', [])
                items_str = ', '.join([f"{x.get('cropType')}x{x.get('amount')}" for x in items])
                reports.append(f"🥷 被 {payload.get('stolenByName')} 偷菜：{items_str}")
            elif etype == 'NEW_MESSAGE':
                reports.append(f"💬 {payload.get('authorName')} 留言：{payload.get('content')}")
            elif etype == 'LEVEL_UP':
                reports.append(f"🎉 升级到 Lv.{payload.get('newLevel')}！")

        if mature_or_wilted:
            hresp = api('farm.harvest', 'POST', {})
            try:
                hdata = hresp.json().get('result', {}).get('data', {})
                crops = hdata.get('crops', [])
                if crops:
                    crops_str = ', '.join([f"{x.get('cropType')}x{x.get('quantity')}" for x in crops])
                    reports.append(f"🌾 收获：{crops_str}，经验+{hdata.get('xpAwarded', 0)}")
                elif hdata.get('harvestedCount', 0) > 0:
                    reports.append(f"🌾 清理了 {hdata.get('harvestedCount')} 块枯萎/成熟地块")
                else:
                    reports.append("🌾 暂无成熟/枯萎作物可收获")
            except Exception as e:
                reports.append(f"farm.harvest 失败: {e}, {hresp.text[:200]}")

        if event_ids:
            ack = api('farm.events.ack', 'POST', {'eventIds': event_ids})
            try:
                ack_data = ack.json()
                if 'error' in ack_data:
                    reports.append(f"events.ack 错误: {ack_data['error']}")
            except Exception as e:
                reports.append(f"events.ack 解析失败: {e}, {ack.text[:200]}")

    status = api('farm.status').json().get('result', {}).get('data', {})
    coins = status.get('coins', 0)
    level = status.get('level', 1)
    plot_count = status.get('plotCount', 0)
    plots = status.get('plots', [])
    warehouse = status.get('warehouse', [])
    idle_slots = [p['slot'] for p in plots if p['status'] == 'idle']

    if plot_count < 18 and idle_slots:
        try:
            buy_resp = api('farm.buyLand', 'POST', {})
            buy_data = buy_resp.json()
            if 'error' not in buy_data:
                new_plot = buy_data.get('result', {}).get('data', {}).get('newPlotSlot')
                reports.append(f"🛒 买地成功，新地块 #{new_plot}")
                status = api('farm.status').json().get('result', {}).get('data', {})
                plots = status.get('plots', [])
                coins = status.get('coins', 0)
                idle_slots = [p['slot'] for p in plots if p['status'] == 'idle']
        except Exception as e:
            pass

    crop_priority = [
        ('radish', 10), ('carrot', 25), ('corn', 40), ('tomato', 60), ('eggplant', 80),
        ('strawberry', 100), ('pumpkin', 120), ('banana', 150), ('orange', 180), ('pomegranate', 220)
    ]
    try:
        unplanted = api('farm.unplantedCrops').json().get('result', {}).get('data', [])
    except Exception:
        unplanted = []

    def pick_crop(coins, level, unplanted):
        for c, price in crop_priority:
            if c in unplanted and coins >= price:
                return c, price
        for c, price in crop_priority:
            if coins >= price:
                return c, price
        return None, 0

    planted = 0
    for slot in idle_slots:
        crop, price = pick_crop(coins, level, unplanted)
        if not crop:
            break
        try:
            plant_resp = api('farm.plant', 'POST', {'plotSlot': slot, 'cropType': crop})
            plant_data = plant_resp.json()
            if 'error' in plant_data:
                err = plant_data['error'].get('message', str(plant_data['error']))
                if 'PLOT_NOT_IDLE' not in err:
                    reports.append(f"plant #{slot} {crop} 失败: {err}")
            else:
                planted += 1
                coins -= price
                if crop in unplanted:
                    unplanted.remove(crop)
        except Exception as e:
            reports.append(f"plant #{slot} 异常: {e}")

    if planted > 0:
        reports.append(f"🌱 种植了 {planted} 块地")

    try:
        friends = api('farm.friends').json().get('result', {}).get('data', [])
        stolen_total = []
        for friend in friends:
            if not friend.get('farmActivated'):
                continue
            uid = friend.get('userId')
            try:
                fview = api('farm.view', 'GET', params={'input': json.dumps({'userId': uid})})
                fdata = fview.json().get('result', {}).get('data', {})
                mature = [p for p in fdata.get('plots', []) if p.get('status') == 'mature']
                if mature:
                    steal_resp = api('farm.steal', 'POST', {'userId': uid})
                    steal_data = steal_resp.json().get('result', {}).get('data', {})
                    stolen = steal_data.get('stolen', [])
                    if stolen:
                        items_str = ', '.join([f"{x.get('cropType')}x{x.get('amount')}" for x in stolen])
                        stolen_total.append(f"从 {friend.get('name')} 偷到 {items_str}")
            except Exception as e:
                continue
        if stolen_total:
            reports.append("🥷 " + '; '.join(stolen_total))
    except Exception as e:
        reports.append(f"偷菜流程异常: {e}")

    total_warehouse = sum(x.get('quantity', 0) for x in warehouse)
    if total_warehouse >= 50:
        try:
            sell_resp = api('farm.sell', 'POST', {})
            sell_data = sell_resp.json().get('result', {}).get('data', {})
            reports.append(f"💰 清仓卖出获得 {sell_data.get('coinsEarned', 0)} 金币，余额 {sell_data.get('coinsTotal', coins)}")
        except Exception as e:
            reports.append(f"sell 异常: {e}")

    state['lastMessageCheck'] = now
    save_state()

if ver_due:
    try:
        remote_skill = requests.get('https://farm.43chat.cn/skills/skill.json', timeout=30).json()
        remote_version = remote_skill.get('version', '0.0.0')
        local_skill_json = local_skill / 'skill.json'
        local_version = '0.0.0'
        if local_skill_json.exists():
            with open(local_skill_json) as f:
                local_version = json.load(f).get('version', '0.0.0')
        if remote_version != local_version:
            files = ['skill.json', 'SKILL.md', 'INSTALL.md', 'HEARTBEAT.md', 'GAMEPLAY.md']
            for fn in files:
                try:
                    url = f"https://farm.43chat.cn/skills/{fn.lower()}"
                    content = requests.get(url, timeout=30).text
                    with open(local_skill / fn, 'w') as f:
                        f.write(content)
                except Exception as e:
                    reports.append(f"下载 {fn} 失败: {e}")
            reports.append(f"📦 版本更新 {local_version} -> {remote_version}")
    except Exception as e:
        reports.append(f"版本检查失败: {e}")
    state['lastVersionCheck'] = now
    save_state()

if reports:
    print('\n'.join(reports))
else:
    print('HEARTBEAT_OK')
