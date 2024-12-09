import dayjs from 'dayjs'
import advancedFormat from 'dayjs/plugin/advancedFormat'
import timezone from 'dayjs/plugin/timezone'
import utc from 'dayjs/plugin/utc'
import localizedFormat from 'dayjs/plugin/localizedFormat'

// Extend dayjs with plugins
dayjs.extend(advancedFormat)
dayjs.extend(timezone)
dayjs.extend(utc)
dayjs.extend(localizedFormat)

export default dayjs 