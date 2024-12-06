export interface LocalArea {
    x_dev: number
    y_dev: number
    dx: number
    dy: number
    nx: number
    ny: number
    startpoint_direction: number
  }
  
  export interface PreviewData {
    center_x: number
    center_y: number
    range: number
    angle: number
    total_points: number
    data: any[]
    layout: any
  }
  
  export interface Measurement {
    timestamp: number
    type: string
    total_points: number
    duration: number
    script?: string
  }