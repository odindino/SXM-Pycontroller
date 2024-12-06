// types/auto-move.d.ts
export interface MoveScript {
    name: string
    script: string
    distance: number
    waitTime: number
    repeatCount: number
    created_time?: string
  }
  
  export interface MovePreviewParams {
    movement_script: string
    distance: number
    center_x: number | null
    center_y: number | null
    angle: number | null
  }