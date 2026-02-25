import { useEffect, useRef } from 'react'

export function useClickOutside<T extends HTMLElement>(callback: () => void) {
  const ref = useRef<T | null>(null)

  useEffect(() => {
    function handleMouseDown(event: MouseEvent) {
      if (!ref.current?.contains(event.target as Node)) callback()
    }
    document.addEventListener('mousedown', handleMouseDown)
    return () => document.removeEventListener('mousedown', handleMouseDown)
  }, [callback])

  return ref
}
