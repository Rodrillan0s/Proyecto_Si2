import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix para iconos con CDN confiable
const icon = L.icon({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

// Sub-componente para mover la cámara del mapa
function ChangeView({ center }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center);
  }, [center, map]);
  return null;
}

const MapEvents = ({ onMapClick }) => {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng);
    },
  });
  return null;
};

export default function MapPicker({ latitud, longitud, onCoordinatesChange }) {
  // Santa Cruz de la Sierra por defecto si no hay coordenadas
  const lat = latitud ? parseFloat(latitud) : -17.783;
  const lng = longitud ? parseFloat(longitud) : -63.182;

  const handleMapClick = (latlng) => {
    onCoordinatesChange(latlng.lat, latlng.lng);
  };

  return (
    <div className="relative w-full h-72 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-inner bg-slate-100 dark:bg-slate-900">
      <MapContainer
        center={[lat, lng]}
        zoom={13}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
      >
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ChangeView center={[lat, lng]} />
        <MapEvents onMapClick={handleMapClick} />
        {latitud && longitud && (
          <Marker position={[lat, lng]} icon={icon} />
        )}
      </MapContainer>
      
      {/* Overlay informativo estilo corporativo */}
      <div className="absolute top-3 right-3 z-[400] bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm px-3 py-1.5 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 pointer-events-none">
        <p className="text-[10px] font-bold text-[#1A5729] dark:text-[#7BC636] uppercase tracking-widest flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
          Selector de Ubicación
        </p>
      </div>
    </div>
  );
}