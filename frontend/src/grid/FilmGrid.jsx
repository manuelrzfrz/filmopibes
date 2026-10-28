import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  flexRender,
} from '@tanstack/react-table';
import { EditableCell } from './EditableCell';
import { upsertRating } from '../../api/filmsApi';

export default function FilmGrid({ data, users, onRefresh }) {
  const [sorting, setSorting] = useState([]);
  const [globalFilter, setGlobalFilter] = useState('');

  // Mapeo dinámico de columnas
  const columns = useMemo(() => {
    // Columnas base de la película
    const baseColumns = [
      {
        accessorKey: 'titulo',
        header: 'Título',
        cell: (info) => (
          <div className="font-medium text-slate-100 flex items-center gap-2">
            {info.row.original.poster_path && (
              <img
                src={`https://image.tmdb.org/t/p/w92${info.row.original.poster_path}`}
                alt=""
                className="w-6 h-9 object-cover rounded shadow"
              />
            )}
            <span>{info.getValue()}</span>
          </div>
        ),
      },
      {
        accessorKey: 'anio',
        header: 'Año',
        cell: (info) => <span className="text-slate-400">{info.getValue() || '-'}</span>,
      },
      {
        accessorKey: 'directores',
        header: 'Director',
        cell: (info) => <span className="text-slate-300">{info.getValue() || '-'}</span>,
      },
      {
        accessorKey: 'generos',
        header: 'Géneros',
        cell: (info) => {
          const generos = info.getValue() || [];
          return (
            <div className="flex flex-wrap gap-1">
              {generos.slice(0, 2).map((g) => (
                <span key={g} className="px-1.5 py-0.5 text-xs bg-slate-800 text-slate-300 rounded">
                  {g}
                </span>
              ))}
            </div>
          );
        },
      },
    ];

    // Función guardar cambios para cualquier usuario
    const handleSaveRating = async (peliculaId, fieldKey, newValue) => {
      // fieldKey viene formateado como "userId_nota" o "userId_vista"
      const [usuarioId, field] = fieldKey.split('_');
      
      const payload = {
        pelicula_id: peliculaId,
        usuario_id: usuarioId,
        [field]: newValue === '' ? null : newValue,
      };

      try {
        await upsertRating(payload);
        if (onRefresh) onRefresh();
      } catch (err) {
        console.error('Error al guardar valoración:', err);
      }
    };

    // Columnas editables para cada Admin (Manolo, Jotace)
    const userColumns = users.flatMap((user) => [
      {
        id: `${user._id}_vista`,
        header: `👁️ ${user.nombre}`,
        accessorFn: (row) => row.valoraciones?.[user._id]?.vista ?? false,
        cell: (props) => (
          <EditableCell {...props} type="checkbox" onSave={handleSaveRating} />
        ),
      },
      {
        id: `${user._id}_nota`,
        header: `⭐ ${user.nombre}`,
        accessorFn: (row) => row.valoraciones?.[user._id]?.nota ?? null,
        cell: (props) => (
          <EditableCell {...props} type="number" onSave={handleSaveRating} />
        ),
      },
    ]);

    return [...baseColumns, ...userColumns];
  }, [users, onRefresh]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div className="flex flex-col h-full w-full bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-xl">
      {/* Buscador Rápido de Tabla */}
      <div className="p-3 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
        <input
          type="text"
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder="Filtrar en la tabla..."
          className="px-3 py-1.5 bg-slate-900 border border-slate-700 text-slate-100 rounded text-sm w-72 focus:outline-none focus:border-amber-500"
        />
        <span className="text-xs text-slate-400 font-mono">
          {table.getFilteredRowModel().rows.length} películas
        </span>
      </div>

      {/* Render de la Tabla */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead className="sticky top-0 bg-slate-950 text-slate-300 border-b border-slate-800 font-semibold z-10">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="px-3 py-2.5 cursor-pointer hover:bg-slate-800 transition-colors select-none"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{ asc: ' 🔼', desc: ' 🔽' }[header.column.getIsSorted()] ?? null}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-slate-800/40 transition-colors">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-1.5 align-middle">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}