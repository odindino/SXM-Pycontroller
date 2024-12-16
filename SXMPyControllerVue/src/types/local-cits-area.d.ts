export interface LocalCITSArea {
    name: string;
    areas: {
      start_x: number;
      start_y: number;
      dx: number;
      dy: number;
      nx: number;
      ny: number;
      startpoint_direction: 1 | -1;
    }[];
    created_time?: string;
    description?: string;
  }
  
  export interface LocalCITSAreaScript {
    name: string;
    areas: LocalCITSArea['areas'];
    created_time: string;
    description?: string;
  }