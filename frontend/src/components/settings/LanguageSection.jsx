import React, { useState } from 'react';
import { Globe } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { languages, timezones } from '../../mock/mockData';

const LanguageSection = () => {
  const [lang, setLang] = useState('fr');
  const [tz, setTz] = useState('cet');

  return (
    <section className="zy-card rounded-2xl p-6 lg:p-8">
      <div className="flex items-start gap-4 mb-6">
        <div className="w-12 h-12 rounded-xl zy-tile flex items-center justify-center flex-shrink-0">
          <Globe className="w-5 h-5 text-[#2952a3] dark:text-[#d4b78c]" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Language &amp; Region</h2>
          <p className="text-sm text-muted-foreground">Définissez votre langue et fuseau horaire</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Langue</label>
          <Select value={lang} onValueChange={setLang}>
            <SelectTrigger className="zy-input h-11 rounded-xl">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {languages.map((l) => (
                <SelectItem key={l.code} value={l.code}>
                  {l.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Fuseau horaire</label>
          <Select value={tz} onValueChange={setTz}>
            <SelectTrigger className="zy-input h-11 rounded-xl">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timezones.map((t) => (
                <SelectItem key={t.code} value={t.code}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </section>
  );
};

export default LanguageSection;
