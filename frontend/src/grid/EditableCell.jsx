import { useState } from 'react';

/**
 * Celda interactiva estilo Excel (Input numérico o Checkbox)
 */
export function EditableCell({ value: initialValue, row, column, type = 'number', onSave }) {
  const [value, setValue] = useState(initialValue ?? '');
  const [previousInitialValue, setPreviousInitialValue] = useState(initialValue);

  // Sincronizar el estado local cuando cambian los datos externos
  if (initialValue !== previousInitialValue) {
    setPreviousInitialValue(initialValue);
    setValue(initialValue ?? '');
  }

  const handleBlur = () => {
    if (value !== initialValue) {
      onSave(row.original._id, column.id, value);
    }
  };

  const handleChangeCheckbox = (e) => {
    const checked = e.target.checked;
    setValue(checked);
    onSave(row.original._id, column.id, checked);
  };

  if (type === 'checkbox') {
    return (
      <div className="flex items-center justify-center h-full">
        <input
          type="checkbox"
          checked={!!value}
          onChange={handleChangeCheckbox}
          className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-amber-500 focus:ring-amber-500 cursor-pointer"
        />
      </div>
    );
  }

  return (
    <input
      type="number"
      min="0"
      max="10"
      step="0.5"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onBlur={handleBlur}
      placeholder="-"
      className="w-full text-center bg-transparent focus:bg-slate-800 text-slate-100 py-1 rounded outline-none border border-transparent focus:border-amber-500 transition-colors font-semibold"
    />
  );
}