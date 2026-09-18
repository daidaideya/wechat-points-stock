function toFiniteNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

export function formatMoney(value) {
  const amount = toFiniteNumber(value, null)
  if (amount == null) return '0'
  return amount.toFixed(2).replace(/\.?0+$/, '')
}

export function formatCashAmount(value) {
  if (value == null || value === '') return '—'
  const amount = toFiniteNumber(value, null)
  if (amount == null) return '—'
  return `¥${formatMoney(amount)}`
}

export function formatProductPrice(product) {
  const points = toFiniteNumber(product?.points)
  const cash = toFiniteNumber(product?.cash)
  if (cash > 0 && points > 0) return `${points} 积分 + ${formatCashAmount(cash)}`
  if (cash > 0) return formatCashAmount(cash)
  return `${points} 积分`
}

export function isRedeemable(product, maxPoints = 0, maxCash = null) {
  const needPoints = toFiniteNumber(product?.points)
  const needCash = toFiniteNumber(product?.cash)
  const stock = toFiniteNumber(product?.stock)
  const availablePoints = toFiniteNumber(maxPoints)

  if (stock <= 0 || needPoints > availablePoints) return false
  if (needCash <= 0) return true

  const availableCash = maxCash == null || maxCash === '' ? null : toFiniteNumber(maxCash, null)
  return availableCash != null && needCash <= availableCash
}

export function getRedeemBlockedLabel(product, maxPoints = 0, maxCash = null) {
  if (toFiniteNumber(product?.stock) <= 0) return '无货'

  const needPoints = toFiniteNumber(product?.points)
  const needCash = toFiniteNumber(product?.cash)
  const availablePoints = toFiniteNumber(maxPoints)
  const availableCash = maxCash == null || maxCash === '' ? null : toFiniteNumber(maxCash, null)
  const pointsShort = needPoints > availablePoints
  const cashShort = needCash > 0 && (availableCash == null || needCash > availableCash)

  if (pointsShort && cashShort) return '积分/现金不足'
  if (cashShort) return '现金不足'
  if (pointsShort) return '积分不足'
  return '不可兑换'
}
