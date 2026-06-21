import React from 'react';
import { Trash2 } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../ui/alert-dialog';
import { toast } from 'sonner';

const DangerZone = () => {
  return (
    <section className="zy-danger rounded-2xl p-6">
      <h3 className="text-base font-semibold text-red-500 mb-4">Zone dangereuse</h3>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <button className="w-full inline-flex items-center justify-center gap-2 h-11 rounded-xl border border-red-500/40 text-red-500 hover:bg-red-500/10 text-sm font-medium transition">
            <Trash2 className="w-4 h-4" />
            Supprimer le compte
          </button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer votre compte ?</AlertDialogTitle>
            <AlertDialogDescription>
              Cette action est irréversible. Toutes vos données, projets et factures seront
              définitivement supprimés.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-500 hover:bg-red-600 text-white"
              onClick={() => toast.error('Compte marqué pour suppression (mock)')}
            >
              Oui, supprimer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <p className="text-[11px] text-muted-foreground mt-3">
        Une fois supprimé, votre compte ne pourra pas être restauré.
      </p>
    </section>
  );
};

export default DangerZone;
