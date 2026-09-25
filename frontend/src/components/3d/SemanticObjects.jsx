/**
 * SemanticObjects.jsx
 * 3D Oriented Bounding Boxes & Dynamic Tracked Object Annotations.
 */

import React from 'react';
import * as THREE from 'three';
import { Html } from '@react-three/drei';

export default function SemanticObjects({ objects = [], visible = true }) {
  const objectList = Array.isArray(objects)
    ? objects
    : (Array.isArray(objects?.annotations) ? objects.annotations : []);

  if (!visible || objectList.length === 0) return null;

  return (
    <group>
      {objectList.map((obj, i) => {
        // Map from KITTI to Three.js: X_three = -obj.y, Y_three = obj.z, Z_three = -obj.x
        const posX = -(obj.y || 0);
        const posY = obj.z || 0;
        const posZ = -(obj.x || 0);

        const width = obj.width || obj.dim_y || 1.8;
        const height = obj.height || obj.dim_z || 1.5;
        const length = obj.length || obj.dim_x || 4.2;

        const isDynamic = obj.is_dynamic || false;
        const color = isDynamic ? '#ef4444' : '#3b82f6';

        return (
          <group key={i} position={[posX, posY, posZ]}>
            {/* 3D Wireframe Bounding Box */}
            <mesh>
              <boxGeometry args={[width, height, length]} />
              <meshBasicMaterial color={color} wireframe={true} transparent={true} opacity={0.7} />
            </mesh>

            {/* Translucent Fill */}
            <mesh>
              <boxGeometry args={[width, height, length]} />
              <meshStandardMaterial color={color} transparent={true} opacity={0.15} />
            </mesh>

            {/* Object HUD Label Badge */}
            <Html position={[0, height / 2 + 0.4, 0]} center distanceFactor={15}>
              <div className="bg-[#0b1329]/90 border border-slate-700 px-2 py-0.5 rounded text-[10px] font-mono-num whitespace-nowrap text-white shadow-lg flex items-center gap-1.5 backdrop-blur-sm">
                <span
                  className="w-2 h-2 rounded-full inline-block"
                  style={{ backgroundColor: color }}
                />
                <span className="font-semibold text-slate-200">{obj.name || obj.label || obj.class_name || 'Object'}</span>
                {obj.speed !== undefined && (
                  <span className="text-cyan-400 font-bold">{Math.round(obj.speed)} km/h</span>
                )}
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}
