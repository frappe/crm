const NUMBER_FORMAT_INFO = {
  '#,###.##': { decimalStr: '.', groupSep: ',' },
  '#.###,##': { decimalStr: ',', groupSep: '.' },
  '# ###.##': { decimalStr: '.', groupSep: ' ' },
  '# ###,##': { decimalStr: ',', groupSep: ' ' },
  "#'###.##": { decimalStr: '.', groupSep: "'" },
  '#, ###.##': { decimalStr: '.', groupSep: ', ' },
  '#,##,###.##': { decimalStr: '.', groupSep: ',' },
  '#,###.###': { decimalStr: '.', groupSep: ',' },
  '#.###': { decimalStr: '', groupSep: '.' },
  '#,###': { decimalStr: '', groupSep: ',' },
}

export function replaceAll(s, t1, t2) {
  return s.split(t1).join(t2)
}

export function strip(s, chars) {
  if (s) {
    s = lstrip(s, chars)
    s = rstrip(s, chars)
    return s
  }
}

export function lstrip(s, chars) {
  if (!chars) chars = ['\n', '\t', ' ']
  // strip left
  let first_char = s.substr(0, 1)
  while (chars.includes(first_char)) {
    s = s.substr(1)
    first_char = s.substr(0, 1)
  }
  return s
}

export function rstrip(s, chars) {
  if (!chars) chars = ['\n', '\t', ' ']
  let last_char = s.substr(s.length - 1)
  while (chars.includes(last_char)) {
    s = s.substr(0, s.length - 1)
    last_char = s.substr(s.length - 1)
  }
  return s
}

export function cstr(s) {
  if (s == null) return ''
  return s + ''
}

export function cint(v, def) {
  if (v === true) return 1
  if (v === false) return 0
  v = v + ''
  if (v !== '0') v = lstrip(v, ['0'])
  v = parseInt(v) // eslint-ignore-line
  if (isNaN(v)) v = def === undefined ? 0 : def
  return v
}

export function flt(v, decimals, numberFormat, roundingMethod) {
  if (v == null || v == '') return 0

  if (typeof v !== 'number') {
    v = v + ''

    // strip currency symbol if exists
    if (v.indexOf(' ') != -1) {
      // using slice(1).join(" ") because space could also be a group separator
      var parts = v.split(' ')
      v = isNaN(parseFloat(parts[0]))
        ? parts.slice(parts.length - 1).join(' ')
        : v
    }

    v = stripNumberGroups(v, numberFormat)

    v = parseFloat(v)
    if (isNaN(v)) v = 0
  }

  if (decimals != null) return roundNumber(v, decimals, roundingMethod)
  return v
}

function stripNumberGroups(v, numberFormat) {
  if (!numberFormat) numberFormat = getNumberFormat()
  var info = getNumberFormatInfo(numberFormat)

  // strip groups (,)
  var groupRegex = new RegExp(
    info.groupSep === '.' ? '\\.' : info.groupSep,
    'g',
  )
  v = v.replace(groupRegex, '')

  // replace decimal separator with (.)
  if (info.decimalStr !== '.' && info.decimalStr !== '') {
    var decimal_regex = new RegExp(info.decimalStr, 'g')
    v = v.replace(decimal_regex, '.')
  }

  return v
}

export function formatNumber(v, format, decimals) {
  if (!format) {
    format = getNumberFormat()
    if (decimals == null)
      decimals = cint(window.sysdefaults.float_precision || 3)
  }

  let info = getNumberFormatInfo(format)

  // Fix the decimal first, toFixed will auto fill trailing zero.
  if (decimals == null) decimals = info.precision

  v = flt(v, decimals, format)

  let isNegative = false
  if (v < 0) isNegative = true
  v = Math.abs(v)

  v = v.toFixed(decimals)

  let part = v.split('.')

  // get group position and parts
  let groupPosition = info.groupSep ? 3 : 0

  if (groupPosition) {
    let integer = part[0]
    let str = ''
    for (let i = integer.length; i >= 0; i--) {
      let l = replaceAll(str, info.groupSep, '').length
      if (format == '#,##,###.##' && str.indexOf(',') != -1) {
        // INR
        groupPosition = 2
        l += 1
      }

      str += integer.charAt(i)

      if (l && !((l + 1) % groupPosition) && i != 0) {
        str += info.groupSep
      }
    }
    part[0] = str.split('').reverse().join('')
  }
  if (part[0] + '' == '') {
    part[0] = '0'
  }

  // join decimal
  part[1] = part[1] && info.decimalStr ? info.decimalStr + part[1] : ''

  // join
  return (isNegative ? '-' : '') + part[0] + part[1]
}

export function formatCurrency(value, format, currency = 'USD', precision = 2) {
  value = value == null || value === '' ? 0 : value

  if (typeof precision != 'number') {
    precision = cint(precision || window.sysdefaults.currency_precision || 2)
  }

  // If you change anything below, it's going to hurt a company in UAE, a bit.
  // if (precision > 2) {
  //   let parts = cstr(value).split('.') // should be minimum 2, comes from the DB
  //   let decimals = parts.length > 1 ? parts[1] : '' // parts.length == 2 ???

  //   if (decimals.length < 3 || decimals.length < precision) {
  //     const fraction = 100

  //     if (decimals.length < cstr(fraction).length) {
  //       precision = cstr(fraction).length - 1
  //     }
  //   }
  // }

  format = getNumberFormat(format)

  if (currency) {
    let symbol = getCurrencySymbol(currency)

    if (symbol) {
      return __(symbol) + ' ' + formatNumber(value, format, precision)
    }
  }

  return formatNumber(value, format, precision)
}

function getNumberFormat(format = null) {
  return format || window.sysdefaults.number_format || '#,###.##'
}

function getCurrencySymbol(currencyCode) {
  try {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })
    // Extract the currency symbol from the formatted string
    const parts = formatter.formatToParts(1)
    const symbol = parts.find((part) => part.type === 'currency')
    return symbol ? symbol.value : null
  } catch (error) {
    console.error(`Invalid currency code: ${currencyCode}`)
    return null
  }
}

function getNumberFormatInfo(format) {
  let info = NUMBER_FORMAT_INFO[format]

  if (!info) {
    info = { decimalStr: '.', groupSep: ',' }
  }

  // get the precision from the number format
  info.precision = format.split(info.decimalStr).slice(1)[0].length

  return info
}

function roundNumber(num, precision, roundingMethod) {
  roundingMethod =
    roundingMethod ||
    window.sysdefaults.rounding_method ||
    "Banker's Rounding (legacy)"

  let isNegative = num < 0 ? true : false

  if (roundingMethod == "Banker's Rounding (legacy)") {
    var d = cint(precision)
    var m = Math.pow(10, d)
    var n = +(d ? Math.abs(num) * m : Math.abs(num)).toFixed(8) // Avoid rounding errors
    var i = Math.floor(n),
      f = n - i
    var r = !precision && f == 0.5 ? (i % 2 == 0 ? i : i + 1) : Math.round(n)
    r = d ? r / m : r
    return isNegative ? -r : r
  } else if (roundingMethod == "Banker's Rounding") {
    if (num == 0) return 0.0
    precision = cint(precision)

    let multiplier = Math.pow(10, precision)
    num = Math.abs(num) * multiplier

    let floorNum = Math.floor(num)
    let decimalPart = num - floorNum

    // For explanation of this method read python flt implementation notes.
    let epsilon = 2.0 ** (Math.log2(Math.abs(num)) - 52.0)

    if (Math.abs(decimalPart - 0.5) < epsilon) {
      num = floorNum % 2 == 0 ? floorNum : floorNum + 1
    } else {
      num = Math.round(num)
    }
    num = num / multiplier
    return isNegative ? -num : num
  } else if (roundingMethod == 'Commercial Rounding') {
    if (num == 0) return 0.0

    let digits = cint(precision)
    let multiplier = Math.pow(10, digits)

    num = num * multiplier

    // For explanation of this method read python flt implementation notes.
    let epsilon = 2.0 ** (Math.log2(Math.abs(num)) - 52.0)
    if (isNegative) {
      epsilon = -1 * epsilon
    }

    num = Math.round(num + epsilon)
    return num / multiplier
  } else {
    throw new Error(`Unknown rounding method ${roundingMethod}`)
  }
}
