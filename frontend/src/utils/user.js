export function isPhoneLike(value) {
  return /^1[3-9]\d{9}$/.test(String(value || '').trim())
}

/** Prefer phone column; fall back if legacy rows put phone into wechat_id. */
export function displayPhone(item) {
  const phone = String(item?.phone || '').trim()
  if (phone) return phone
  const wid = String(item?.wechat_id || '').trim()
  return isPhoneLike(wid) ? wid : ''
}

/** Real WeChat id only — hide when wechat_id is actually a phone number. */
export function displayWechatId(item) {
  const wid = String(item?.wechat_id || '').trim()
  if (!wid || isPhoneLike(wid)) return ''
  return wid
}

export function displayName(item) {
  const nick = String(item?.nickname || '').trim()
  if (nick) return nick
  const phone = displayPhone(item)
  if (phone) return phone
  return displayWechatId(item) || '未命名用户'
}

export function displayPrimaryId(item) {
  const phone = displayPhone(item)
  const wx = displayWechatId(item)
  if (phone && wx) return `手机 ${phone}`
  if (phone) return `手机 ${phone}`
  if (wx) return `微信 ${wx}`
  return '未设置账号标识'
}

export function avatarChar(item) {
  const text = String(displayName(item) || '?').trim()
  if (!text) return '?'
  const first = Array.from(text)[0] || '?'
  return first.toUpperCase()
}

export function avatarColor(item) {
  const seed = String(displayPhone(item) || displayWechatId(item) || item?.nickname || '').trim()
  if (!seed) return 'linear-gradient(135deg, #e7b35a, #d89a3c)'
  let hash = 0
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) | 0
  }
  const hue = Math.abs(hash) % 360
  const hue2 = (hue + 35) % 360
  return `linear-gradient(135deg, hsl(${hue}, 62%, 58%), hsl(${hue2}, 70%, 48%))`
}
