export type MenuItemData = {
  title_fa: string
  title_en: string
  image: string
  variants: {
    title: string
    price: number
    calerios: number
  }[]
  ingredient: string
}

export type Category = {
  id: number
  title: string
  image: string
  items: MenuItemData[]
}
